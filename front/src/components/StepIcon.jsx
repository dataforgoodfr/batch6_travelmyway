import React from 'react'
import bus from '../img/svg/bus.svg'
import car from '../img/svg/car.svg'
import plane from '../img/svg/plane.svg'
import subway from '../img/svg/subway.svg'
import train from '../img/svg/train.svg'
import wait from '../img/svg/wait.svg'
import walk from '../img/svg/walk.svg'

const StepIcon = ({ stepType }) => {
  const stepIcon = {
    Walking: walk,
    Coach: bus,
    ratp: subway,
    Plane: plane,
    car,
    métro: subway,
    Waiting: wait,
    Train: train
  }
  return <img src={stepIcon[stepType]} alt={stepType} />
}

export default StepIcon
