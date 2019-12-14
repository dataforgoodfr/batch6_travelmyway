import moment from 'moment'

export const getTimeFromDate = date => moment(date).format('HH:mm')

export const getDurationFromSeconds = secs => {
  if (secs < 60) return `${moment.utc(secs * 1000).format('ss')}s`
  if (secs > 3600)
    return moment
      .utc(secs * 1000)
      .format('HH:mm')
      .replace(':', 'h')
  return `${moment.utc(secs * 1000).format('mm')}m`
}

export const getCO2InKg = CO2InG => `${Math.round((CO2InG / 1000) * 100) / 100} kg`
