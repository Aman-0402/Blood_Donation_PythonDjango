import { Navigate, Route, Routes } from 'react-router-dom'
import DashboardLayout from '../layouts/DashboardLayout'
import Home from '../pages/Home'
import Login from '../pages/Login'
import Register from '../pages/Register'
import RoleHome from '../pages/RoleHome'
import AdminHospitals from '../pages/admin/AdminHospitals'
import BloodAvailability from '../pages/hospital/BloodAvailability'
import HospitalDashboard from '../pages/hospital/HospitalDashboard'
import HospitalProfile from '../pages/hospital/HospitalProfile'
import DonorDashboard from '../pages/donor/DonorDashboard'
import DonorDonations from '../pages/donor/DonorDonations'
import DonorProfile from '../pages/donor/DonorProfile'
import RequestDetail from '../pages/requests/RequestDetail'
import RequestForm from '../pages/requests/RequestForm'
import RequestList from '../pages/requests/RequestList'
import { ROLES } from '../utils/roles'
import ProtectedRoute from './ProtectedRoute'

function roleRoutes(role, { index = <RoleHome />, children = null } = {}) {
  return (
    <Route element={<ProtectedRoute roles={[role]} />}>
      <Route path={`/${role}`} element={<DashboardLayout />}>
        <Route index element={index} />
        {children}
      </Route>
    </Route>
  )
}

const donorChildren = (
  <>
    <Route path="profile" element={<DonorProfile />} />
    <Route path="donations" element={<DonorDonations />} />
  </>
)

const requesterChildren = (
  <>
    <Route path="requests" element={<RequestList />} />
    <Route path="requests/new" element={<RequestForm />} />
    <Route path="requests/:id" element={<RequestDetail />} />
    <Route path="requests/:id/edit" element={<RequestForm />} />
  </>
)

const adminChildren = (
  <>
    <Route path="requests" element={<RequestList />} />
    <Route path="requests/:id" element={<RequestDetail />} />
    <Route path="hospitals" element={<AdminHospitals />} />
  </>
)

const hospitalChildren = (
  <>
    <Route path="profile" element={<HospitalProfile />} />
    <Route path="availability" element={<BloodAvailability />} />
    {requesterChildren}
  </>
)

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      {roleRoutes(ROLES.ADMIN, { children: adminChildren })}
      {roleRoutes(ROLES.DONOR, { index: <DonorDashboard />, children: donorChildren })}
      {roleRoutes(ROLES.SEEKER, { children: requesterChildren })}
      {roleRoutes(ROLES.HOSPITAL, { index: <HospitalDashboard />, children: hospitalChildren })}
      {roleRoutes(ROLES.BLOODBANK)}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
