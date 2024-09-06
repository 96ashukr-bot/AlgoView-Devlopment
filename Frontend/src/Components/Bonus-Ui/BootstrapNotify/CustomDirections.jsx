import React, { Fragment } from 'react';
import { Col, Card, CardBody, CardHeader } from 'reactstrap';
import { toast } from 'react-toastify';
import { CustomDirections, BottomLeft, BottomCenter, RightBottom, TopCenter } from '../../../Constant';
import { Btn, H5 } from '../../../AbstractElements';

// toast.configure();


const CustomDirectionsClass = () => {

  const directiontoaster = (toastname) => {
    switch (toastname) {
      case 'directionssuccessToast':
        toast.success('Success Notification !', {
          position: toast.POSITION.TOP_CENTER
        });
        break;
      case 'directionsinfoToast':
        toast.info('Info Notification !', {
          position: toast.POSITION.BOTTOM_CENTER
        });
        break;
      case 'directionswarningToast':
        toast.warn('Warning Notification !', {
          position: toast.POSITION.BOTTOM_LEFT
        });
        break;
      case 'directionsdangerToast':
        toast.error('Danger Notification !', {
          position: toast.POSITION.BOTTOM_RIGHT
        });
        break;
      default:
        break;
    }
  };

  return (
    <Fragment>
      <Col sm="12">
        <Card>
          <CardHeader>
            <H5>{CustomDirections}</H5>
          </CardHeader>
          <CardBody>
            <div className="btn-showcase">
              <Btn attrBtn={{ name: 'directionssuccessToast', color: 'success', onClick: (e) => directiontoaster(e.target.name) }}>{TopCenter}</Btn>
              <Btn attrBtn={{ name: 'directionsinfoToast', color: 'info', onClick: (e) => directiontoaster(e.target.name) }}> {BottomCenter}</Btn>
              <Btn attrBtn={{ name: 'directionswarningToast', color: 'warning', onClick: (e) => directiontoaster(e.target.name) }}>{BottomLeft}</Btn>
              <Btn attrBtn={{ name: 'directionsdangerToast', color: 'danger', onClick: (e) => directiontoaster(e.target.name) }}>{RightBottom}</Btn>
            </div>
          </CardBody >
        </Card >
      </Col >
    </Fragment >
  );
};

export default CustomDirectionsClass;