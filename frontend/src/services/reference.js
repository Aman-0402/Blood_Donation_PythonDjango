import api from './api'

let bloodGroupsPromise = null

export function getBloodGroups() {
  bloodGroupsPromise ??= api
    .get('/blood-groups/')
    .then((res) => res.data)
    .catch((err) => {
      bloodGroupsPromise = null
      throw err
    })
  return bloodGroupsPromise
}
