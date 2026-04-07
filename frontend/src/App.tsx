import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { ErrorProvider } from '@/contexts/ErrorContext';
import { AppLayout } from '@/layouts/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { SimulationsPage } from '@/pages/SimulationsPage';
import { SimulationDetailPage } from '@/pages/SimulationDetailPage';
import { JudgePage } from '@/pages/JudgePage';
import { Chat } from '@/pages/Chat';


function App() {
  return (
    <ErrorProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="simulations" element={<SimulationsPage />} />
          <Route path="simulations/:simId" element={<SimulationDetailPage />} />
          <Route path="chat" element={<Chat />} />
          <Route path="judge" element={<JudgePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toaster />
    </ErrorProvider>
  );
}

export default App;
