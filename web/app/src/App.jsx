import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Nav from './components/Nav'
import HomePage from './pages/HomePage'
import StartPage from './pages/StartPage'
import BrowsePage from './pages/BrowsePage'
import FindPage from './pages/FindPage'
import ToolPage from './pages/ToolPage'
import BoxPage from './pages/BoxPage'
import Ask1Page from './pages/Ask1Page'
import Ask2Page from './pages/Ask2Page'
import ResultPage from './pages/ResultPage'
import HelpPage from './pages/HelpPage'

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/start" element={<StartPage />} />
        <Route path="/browse/:categoryId" element={<BrowsePage />} />
        <Route path="/find" element={<FindPage />} />
        <Route path="/tool/:id" element={<ToolPage />} />
        <Route path="/box" element={<BoxPage />} />
        <Route path="/ask/1" element={<Ask1Page />} />
        <Route path="/ask/2" element={<Ask2Page />} />
        <Route path="/result" element={<ResultPage />} />
        <Route path="/help" element={<HelpPage />} />
      </Routes>
    </BrowserRouter>
  )
}
