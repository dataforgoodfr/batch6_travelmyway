import Axios from 'axios'

export const api = Axios.create({
  // baseURL: apiConfig.backendUrl,
  // ⬇️ @TODO placer url dans un .env
  baseURL: 'http://127.0.0.1:5000'
})

export const getJourney = (departureLat, departureLng, arrivalLat, arrivalLng, date) =>
  //api.get('http://127.0.0.1:5000/fake_journey?from=48.85,2.35&to=52.517,13.388&start=2020-11-28')

  // ⬇ Dé-commenter pour avoir la vraie data
  api.get(
    `/journey?from=${departureLat},${departureLng}&to=${arrivalLat},${arrivalLng}&start=2020-11-28`
  )
