import { AppRoutes } from '../core/presentation/routes/AppRoutes';
import { QueryProvider } from '../core/presentation/providers/QueryProvider';

function App() {
  return (
      <QueryProvider>
        <AppRoutes />
      </QueryProvider>
  );
}

export default App;