import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { ErrorProvider } from '@/contexts/ErrorContext';
import { AppLayout } from '@/layouts/AppLayout';
import { SimulationDetailPage } from '@/pages/SimulationDetailPage';
import { Chat } from '@/pages/Chat';
import { SettingsPage } from '@/pages/SettingsPage';
import { ExperimentsPage } from '@/pages/ExperimentsPage';
import { AgentPage } from '@/pages/agents/AgentPage';


function App() {
  return (
    <ErrorProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/experiments" replace />} />
          <Route path="simulations/:simId" element={<SimulationDetailPage />} />
          <Route path="chat" element={<Chat />} />
          <Route path="experiments" element={<ExperimentsPage />} />
          <Route path="agents/doctor" element={<AgentPage agent="doctor" />} />
          <Route path="agents/patient" element={<AgentPage agent="patient" />} />
          <Route path="agents/judge" element={<AgentPage agent="judge" />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/experiments" replace />} />
      </Routes>
      <Toaster />
    </ErrorProvider>
  );
}

export default App;
