import { AppRoutes } from "../core/presentation/routes/AppRoutes";
import { QueryProvider } from "../core/presentation/providers/QueryProvider";
import { AppHydrate } from "../core/presentation/providers/AppHydrate.tsx";

function App() {
    return (
        <QueryProvider>
            <AppHydrate>
                <AppRoutes />
            </AppHydrate>
        </QueryProvider>
    );
}

export default App;