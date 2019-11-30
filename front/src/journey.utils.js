import moment from 'moment'

export const getTimeFromDate = date => moment(date).format('HH:mm')

export const getDurationFromSeconds = secs => {
  if (secs < 60) return `${moment.utc(secs * 1000).format('ss')}sec`
  if (secs > 3600) return moment.utc(secs * 1000).format('HH:mm')
  return `${moment.utc(secs * 1000).format('mm')}min`
}

export const getCO2InKg = CO2InG => `${Math.round((CO2InG / 1000) * 100) / 100} kg`
