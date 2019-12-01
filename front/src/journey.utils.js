import moment from 'moment'

export const getTimeFromDate = date => moment(date).format('HH:mm')

export const getDurationFromSeconds = secs => moment.utc(secs * 1000).format('HH:mm')
