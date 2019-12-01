import moment from 'moment'

export const getTimeFromDate = date => moment(date).format('HH:mm')

export const getDurationFromSeconds = secs => {
  if (secs > 3600) {
    return moment.utc(secs * 1000).format('HH:mm')
  }
  return `${moment.utc(secs * 1000).format('mm')}m`
}
