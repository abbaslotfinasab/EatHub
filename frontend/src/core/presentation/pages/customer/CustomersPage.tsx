import {useCallback, useMemo, useState} from "react";
import {Add} from "@mui/icons-material";
import {
    Box,
    Container,
    Fab,
    Stack,
    Typography,
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

export function CustomersPage() {

    const [search, setSearch] = useState("");

    const [filters] = useState<CustomerSearchFilters>({
        ordering: "-created_at",
    });

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

    const {
        data: customers = [],
    } = useGetAllCustomers({
        ...filters,
        search,
    });

    const stats = useMemo(() => ({

        totalCustomers: customers.length,

        totalBalance: customers.reduce(
            (sum, customer) => sum + (customer.balance ?? 0),
            0,
        ),

        totalOrders: customers.reduce(
            (sum, customer) => sum + (customer.totalOrders ?? 0),
            0,
        ),

        totalSpent: customers.reduce(
            (sum, customer) => sum + (customer.totalSpent ?? 0),
            0,
        ),

    }), [customers]);

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
        <Container
            maxWidth="xl"
            sx={{py: 4}}
        >
            <Stack spacing={3}>

                <Box>
                    <Typography
                        variant="h4"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        مشتریان
                    </Typography>

                    <Typography color="text.secondary">
                        مدیریت مشتریان و حساب‌های اعتباری
                    </Typography>
                </Box>

                <CustomersStats
                    totalCustomers={stats.totalCustomers}
                    totalBalance={stats.totalBalance}
                    totalOrders={stats.totalOrders}
                    totalSpent={stats.totalSpent}
                />

                <CustomersToolbar
                    search={search}
                    onSearchChange={setSearch}
                    onFilterClick={() => {
                    }}
                    onCreateClick={handleCreate}
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

                        if (selectedCustomer) { /* empty */ } else {

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

        </Container>
    );
}