import { Navigate, Route, Routes } from 'react-router-dom'
import DashboardLayout from '../layouts/DashboardLayout'
import Home from '../pages/Home'
import Login from '../pages/Login'
import Register from '../pages/Register'
import RoleHome from '../pages/RoleHome'
import AdminVerification from '../pages/admin/AdminVerification'
import BankDonations from '../pages/bank/BankDonations'
import BankHistory from '../pages/bank/BankHistory'
import BankHome from '../pages/bank/BankHome'
import BankInventory from '../pages/bank/BankInventory'
import BankIssue from '../pages/bank/BankIssue'
import BankProfile from '../pages/bank/BankProfile'
import DonorDashboard from '../pages/donor/DonorDashboard'
import DonorDonations from '../pages/donor/DonorDonations'
import DonorProfile from '../pages/donor/DonorProfile'
import DonorRequests from '../pages/donor/DonorRequests'
import ScheduleDonation from '../pages/donor/ScheduleDonation'
import HospitalDashboard from '../pages/hospital/HospitalDashboard'
import HospitalProfile from '../pages/hospital/HospitalProfile'
import RequestDetail from '../pages/requests/RequestDetail'
import RequestForm from '../pages/requests/RequestForm'
import RequestList from '../pages/requests/RequestList'
import SearchPage from '../pages/search/SearchPage'
import { listBloodBanks, setBloodBankVerified } from '../services/bloodbanks'
import { listHospitals, setHospitalVerified } from '../services/hospitals'
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
    <Route path="schedule" element={<ScheduleDonation />} />
    <Route path="requests" element={<DonorRequests />} />
  </>
)

const requesterChildren = (
  <>
    <Route path="search" element={<SearchPage />} />
    <Route path="requests" element={<RequestList />} />
    <Route path="requests/new" element={<RequestForm />} />
    <Route path="requests/:id" element={<RequestDetail />} />
    <Route path="requests/:id/edit" element={<RequestForm />} />
  </>
)

const readOnlyRequestChildren = (
  <>
    <Route path="search" element={<SearchPage />} />
    <Route path="requests" element={<RequestList />} />
    <Route path="requests/:id" element={<RequestDetail />} />
  </>
)

const adminChildren = (
  <>
    {readOnlyRequestChildren}
    <Route
      path="hospitals"
      element={<AdminVerification title="Hospitals" fetchList={listHospitals} setVerified={setHospitalVerified} />}
    />
    <Route
      path="bloodbanks"
      element={<AdminVerification title="Blood banks" fetchList={listBloodBanks} setVerified={setBloodBankVerified} />}
    />
  </>
)

const hospitalChildren = (
  <>
    <Route path="profile" element={<HospitalProfile />} />
    {requesterChildren}
  </>
)

const bankChildren = (
  <>
    <Route path="profile" element={<BankProfile />} />
    <Route path="inventory" element={<BankInventory />} />
    <Route path="issue" element={<BankIssue />} />
    <Route path="donations" element={<BankDonations />} />
    <Route path="history" element={<BankHistory />} />
    {readOnlyRequestChildren}
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
      {roleRoutes(ROLES.BLOODBANK, { index: <BankHome />, children: bankChildren })}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
