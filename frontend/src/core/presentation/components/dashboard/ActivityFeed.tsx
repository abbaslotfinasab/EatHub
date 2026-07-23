import {
    Card,
    CardContent,
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import HomeIcon from "@mui/icons-material/Home";

import {ActivityItem} from "./ActivityItem";

import type {Activity} from "../../../domain/entities/core/dashboard/Activity";


interface ActivityFeedProps {

    activities: Activity[];

}


export const ActivityFeed = ({
                                 activities,
                             }: ActivityFeedProps) => {


    return (
        <Card
            elevation={0}
            sx={{
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                height: "100%",
            }}
        >
            <CardContent>

                <Stack spacing={3}>

                    <Stack
                        direction="row"
                        sx={{
                            alignItems: "center",
                            gap: 1,
                        }}
                    >

                        <HomeIcon/>

                        <Typography
                            variant="h6"
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            فعالیت‌های اخیر
                        </Typography>

                    </Stack>


                    {activities.map(
                        (activity, index) => (

                            <Stack
                                key={activity.id}
                                spacing={2}
                            >

                                <ActivityItem
                                    userName={
                                        activity.user ?? "-"
                                    }
                                    title={activity.title}
                                    description={activity.description}
                                    action={
                                        activity.action
                                    }
                                    createdAt={
                                        activity.createdAt
                                    }
                                />


                                {
                                    index !== activities.length - 1 && (
                                        <Divider/>
                                    )
                                }

                            </Stack>

                        )
                    )}

                </Stack>

            </CardContent>
        </Card>
    );
};