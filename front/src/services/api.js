import Axios from 'axios'
import fakeJourney from '../../fakeJourney'

export const api = Axios.create({
  // baseURL: apiConfig.backendUrl,
  // ⬇️ @TODO placer url dans un .env
  baseURL: 'http://127.0.0.1:5000'
})

export const getJourney = (departureLat, departureLng, arrivalLat, arrivalLng, date) => 
// fakeJourney
// ⬇ Dé-commenter pour avoir la vraie data
  api.get(
    `/journey?from=${departureLat},${departureLng}&to=${arrivalLat},${arrivalLng}&start=${date}`
  )


