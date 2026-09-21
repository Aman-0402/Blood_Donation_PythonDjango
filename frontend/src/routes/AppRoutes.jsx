import { Navigate, Route, Routes } from 'react-router-dom'
import DashboardLayout from '../layouts/DashboardLayout'
import Home from '../pages/Home'
import Login from '../pages/Login'
import Register from '../pages/Register'
import RoleHome from '../pages/RoleHome'
import DonorDashboard from '../pages/donor/DonorDashboard'
import DonorDonations from '../pages/donor/DonorDonations'
import DonorProfile from '../pages/donor/DonorProfile'
import { ROLES } from '../utils/roles'
import ProtectedRoute from './ProtectedRoute'

function roleRoutes(role, children = null) {
  return (
    <Route element={<ProtectedRoute roles={[role]} />}>
      <Route path={`/${role}`} element={<DashboardLayout />}>
        {children ?? <Route index element={<RoleHome />} />}
      </Route>
    </Route>
  )
}

const donorChildren = (
  <>
    <Route index element={<DonorDashboard />} />
    <Route path="profile" element={<DonorProfile />} />
    <Route path="donations" element={<DonorDonations />} />
  </>
)

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      {roleRoutes(ROLES.ADMIN)}
      {roleRoutes(ROLES.DONOR, donorChildren)}
      {roleRoutes(ROLES.SEEKER)}
      {roleRoutes(ROLES.HOSPITAL)}
      {roleRoutes(ROLES.BLOODBANK)}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
