import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { ErrorProvider } from '@/contexts/ErrorContext';
import { BatchRunProvider } from '@/contexts/BatchRunContext';
import { AppLayout } from '@/layouts/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { ScenariosPage } from '@/pages/ScenariosPage';
import { PersonasPage } from '@/pages/PersonasPage';
import { SimulationsPage } from '@/pages/SimulationsPage';
import { SimulationDetailPage } from '@/pages/SimulationDetailPage';
import { SessionsPage } from '@/pages/SessionsPage';
import { SessionDetailPage } from '@/pages/SessionDetailPage';
import { AnalysisPage } from '@/pages/AnalysisPage';
import { JudgePage } from '@/pages/JudgePage';
import { ParticipantStudyPage } from '@/pages/ParticipantStudyPage';

function App() {
  return (
    <ErrorProvider>
    <BatchRunProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="scenarios" element={<ScenariosPage />} />
          <Route path="personas" element={<PersonasPage />} />
          <Route path="simulations" element={<SimulationsPage />} />
          <Route path="simulations/:simId" element={<SimulationDetailPage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="sessions/:sessionId" element={<SessionDetailPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="judge" element={<JudgePage />} />
        </Route>
        <Route path="participate" element={<ParticipantStudyPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toaster />
    </BatchRunProvider>
    </ErrorProvider>
  );
}

export default App;
