import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { H4 } from '../../../AbstractElements';
import SvgIcon from '../Component/SvgIcon';

const SuperWidgets = ({ data }) => {
    if (!data) {
      return <div>Loading...</div>; 
    }
  
    return (
      <Card className='widget-1'>
        <CardBody>
          <div className='widget-content'>
            <div className={`widget-round ${data.color || 'default-color'}`}>
              <div className='bg-round'>
                <SvgIcon className='svg-fill' iconId={`${data.icon || 'default-icon'}`} />
                <SvgIcon className='half-circle svg-fill' iconId='halfcircle' />
              </div>
            </div>
            <div>
              <H4>{data.total || '0'}</H4>
              <span className='f-light'>{data.title || 'No Title'}</span>
            </div>
          </div>
          {/* <div className={`font-${data.color || 'default-color'} f-w-500`}>
            <i
              className={`icon-arrow-${data.gros < 50 ? 'down' : 'up'} icon-rotate me-1`}
            />
            <span>{`${data.gros < 50 ? '-' : '+'}${data.gros || 0}%`}</span>
          </div> */}
        </CardBody>
      </Card>
    );
  };
  

export default SuperWidgets;
