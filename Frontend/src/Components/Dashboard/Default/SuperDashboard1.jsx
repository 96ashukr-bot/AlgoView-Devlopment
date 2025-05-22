import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { H4 } from '../../../AbstractElements';
import SvgIcon from '../../Common/Component/SvgIcon';

const SuperDashboard1 = ({ data = {} }) => {
  const { color = '', icon = '', total = 0, title = '', gros = 0 } = data; 

  return (
    <Card className='widget-1'>
      <CardBody>
        <div className='widget-content'>
          <div className={`widget-round ${color}`}>
            <div className='bg-round'>
              <SvgIcon className='svg-fill' iconId={icon} />
              <SvgIcon className='half-circle svg-fill' iconId='halfcircle' />
            </div>
          </div>
          <div>
            <H4>{total}</H4>
            <span className='f-light'>{title}</span>
          </div>
        </div>
        <div className={`font-${color} f-w-500`}>
          <i className={`icon-arrow-${gros < 50 ? 'down' : 'up'} icon-rotate me-1`} />
          <span>{`${gros < 50 ? '-' : '+'}${gros}%`}</span>
        </div>
      </CardBody>
    </Card>
  );
};

export default SuperDashboard1;
