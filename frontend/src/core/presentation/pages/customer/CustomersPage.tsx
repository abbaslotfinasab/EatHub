import {useCallback, useMemo, useState} from "react";
import {Add} from "@mui/icons-material";
import {
    Container,
    Fab,
    Stack,
} from "@mui/material";

import type {CustomerListItem} from "../../../domain/entities/product/customer/CustomerListItem";
import type {CustomerSearchFilters} from "../../../domain/objects/filters/CustomerSearchFilters";

import {CustomersStats} from "../../components/customer/CustomersStats";
import {CustomersToolbar} from "../../components/customer/CustomersToolbar";
import {CustomersTable} from "../../components/customer/CustomersTable";
import {CustomerDetailsDialog} from "../../components/customer/CustomerDetailsDialog";
import {CustomerFormDialog} from "../../components/customer/CustomerFormDialog";
import {CustomerBalanceDialog} from "../../components/customer/CustomerBalanceDialog";

import {useCreateCustomer} from "../../hooks/customer/useCreateCustomer";
import {useGetAllCustomers} from "../../hooks/customer/useGetAllCustomers";
import {CustomerBalanceOperation} from "../../../domain/objects/CustomerBalanceOperation.ts";
import {useUpdateCustomerBalance} from "../../hooks/customer/useUpdateCustomerBalance";
import {useDebounce} from "../../hooks/useDebounce.ts";
import AddIcon from "@mui/icons-material/Add";

export function CustomersPage() {

    const [search, setSearch] = useState("");

    const [filters, setFilters] =
        useState<CustomerSearchFilters>({
            ordering: "-created_at",
        });


    const debouncedSearch =
        useDebounce(search, 500);


    const customerFilters = useMemo(
        () => ({

            ...filters,

            search:
                debouncedSearch || undefined,

        }), [
            filters,
            debouncedSearch
        ]);


    const {
        data: customers = []
    } = useGetAllCustomers(
        customerFilters
    );

    const [selectedCustomer, setSelectedCustomer] =
        useState<CustomerListItem | null>(null);

    const [detailsOpen, setDetailsOpen] = useState(false);

    const [formOpen, setFormOpen] = useState(false);

    const [balanceOpen, setBalanceOpen] = useState(false);

    const [operation, setOperation] =
        useState<CustomerBalanceOperation>(
            CustomerBalanceOperation.CREDIT
        );

    const [amount, setAmount] = useState("");

    const [description, setDescription] =
        useState("");

    const createCustomer =
        useCreateCustomer();

    const updateBalanceMutation =
        useUpdateCustomerBalance();

    const stats = useMemo(() => {

        const creditors = customers.reduce(
            (sum, customer) =>
                customer.balance && customer.balance > 0
                    ? sum + customer.balance
                    : sum,
            0,
        );

        const debtors = customers.reduce(
            (sum, customer) =>
                customer.balance && customer.balance < 0
                    ? sum + Math.abs(customer.balance)
                    : sum,
            0,
        );

        return {

            totalCustomers: customers.length,

            totalOrders: customers.reduce(
                (sum, customer) =>
                    sum + (customer.totalOrders ?? 0),
                0,
            ),

            totalSpent: customers.reduce(
                (sum, customer) =>
                    sum + (customer.totalSpent ?? 0),
                0,
            ),

            creditors,
            debtors,

        };

    }, [customers]);

    const handleCreate = useCallback(() => {

        setSelectedCustomer(null);

        setFormOpen(true);

    }, []);

    const handleView = useCallback((customer: CustomerListItem) => {

        setSelectedCustomer(customer);

        setDetailsOpen(true);

    }, []);

    const handleEdit = useCallback((customer: CustomerListItem) => {

        setSelectedCustomer(customer);

        setFormOpen(true);

    }, []);
    const handleRecharge = useCallback((customer: CustomerListItem) => {

        setSelectedCustomer(customer);

        setOperation(
            CustomerBalanceOperation.CREDIT,
        );

        setAmount("");

        setDescription("");

        setBalanceOpen(true);

    }, []);

    const handleDelete = useCallback((customer: CustomerListItem) => {

        console.log(customer);

    }, []);

    return (

        <Container maxWidth="xl">
            <Stack spacing={3}>

                <CustomersStats
                    totalCustomers={stats.totalCustomers}
                    creditors={stats.creditors}
                    debtors={stats.debtors}
                    totalSpent={stats.totalSpent}
                />

                <CustomersToolbar
                    search={search}
                    filters={filters}
                    onSearchChange={setSearch}
                    onFiltersChange={setFilters}
                />

                <CustomersTable
                    customers={customers}
                    onView={handleView}
                    onEdit={handleEdit}
                    onRecharge={handleRecharge}
                    onDelete={handleDelete}
                />

            </Stack>

            <Fab
                color="primary"
                onClick={handleCreate}
                sx={{
                    position: "fixed",
                    bottom: 24,
                    right: 24,
                }}
            >
                <Add/>
            </Fab>

            <CustomerDetailsDialog
                open={detailsOpen}
                customer={selectedCustomer}
                onClose={() => setDetailsOpen(false)}
                onEdit={handleEdit}
                onRecharge={handleRecharge}
            />

            <CustomerFormDialog
                open={formOpen}
                loading={createCustomer.isPending}
                initialValues={
                    selectedCustomer
                        ? {
                            name: selectedCustomer.name,
                            phone: selectedCustomer.phone,
                        }
                        : undefined
                }
                onClose={() => {

                    setFormOpen(false);

                    setSelectedCustomer(null);

                }}
                onSubmit={async (values) => {

                    try {

                        if (selectedCustomer) { /* empty */
                        } else {

                            await createCustomer.mutateAsync(values);

                        }

                        setFormOpen(false);

                        setSelectedCustomer(null);

                    } catch (error) {

                        console.error(error);

                    }

                }}
            />

            <CustomerBalanceDialog
                open={balanceOpen}
                customer={selectedCustomer}
                operation={operation}
                amount={amount}
                description={description}
                onClose={() => setBalanceOpen(false)}
                onOperationChange={setOperation}
                onAmountChange={setAmount}
                onDescriptionChange={setDescription}
                onSubmit={async () => {

                    if (!selectedCustomer) {
                        return;
                    }


                    await updateBalanceMutation.mutateAsync({

                        customerId: selectedCustomer.id,

                        type: operation,

                        amount: Number(amount),

                        description,

                    });


                    setBalanceOpen(false);

                    setAmount("");

                    setDescription("");

                }}
            />

            <Fab
                variant="extended"
                onClick={() => handleCreate()
                }
                sx={{
                    position:
                        "fixed",

                    left: 24,
                    bottom: 24,

                    bgcolor:
                        "#10281A",

                    color: "#fff",

                    "&:hover": {
                        bgcolor:
                            "#173724",
                    },
                }}
            >
                <AddIcon/>
                مشتری جدید
            </Fab>

        </Container>
    );
}