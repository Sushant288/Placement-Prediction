import { Navigate, Route, Routes } from 'react-router-dom';
import Shell from '../components/Shell';
import AnalysisPages from '../pages/AnalysisPages';
import ConnectionPage from '../pages/ConnectionPage';

export default function App() {
  return <Routes><Route element={<Shell />}>
    <Route path="/" element={<AnalysisPages page="overview" />} />
    <Route path="/profile" element={<AnalysisPages page="profile" />} />
    <Route path="/placement" element={<AnalysisPages page="placement" />} />
    <Route path="/skills" element={<AnalysisPages page="skills" />} />
    <Route path="/recommendations" element={<AnalysisPages page="recommendations" />} />
    <Route path="/what-if" element={<AnalysisPages page="whatIf" />} />
    <Route path="/salary" element={<AnalysisPages page="salary" />} />
    <Route path="/eda" element={<AnalysisPages page="eda" />} />
    <Route path="/models" element={<AnalysisPages page="models" />} />
    <Route path="/connection" element={<ConnectionPage />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Route></Routes>;
}
