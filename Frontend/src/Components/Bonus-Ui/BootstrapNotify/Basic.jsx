import React, { Fragment } from 'react';
import { Col, Card, CardBody, CardHeader } from 'reactstrap';
import { toast } from 'react-toastify';
import { BasicExamples, SuccessNotification, InfoNotification, WarningNotification, DangerNotification } from '../../../Constant';
import { Btn, H5 } from '../../../AbstractElements';

// toast.configure();


const Basic = () => {

  const basictoaster = (toastname) => {

    switch (toastname) {
      case 'basicsuccessToast':
        toast.success('Success Notification !', {
          position: toast.POSITION.TOP_RIGHT
        });
        break;
      case 'basicinfoToast':
        toast.info('Info Notification !', {
          position: toast.POSITION.TOP_RIGHT
        });
        break;
      case 'basicwarningToast':
        toast.warn('Warning Notification !', {
          position: toast.POSITION.TOP_RIGHT
        });
        break;
      case 'basicdangerToast':
        toast.error('Danger Notification !', {
          position: toast.POSITION.TOP_RIGHT
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
            <H5>{BasicExamples}</H5>
          </CardHeader>
          <CardBody>
            <div className="btn-showcase">
              <Btn attrBtn={{ name: 'basicsuccessToast', color: 'success', onClick: (e) => basictoaster(e.target.name) }}>{SuccessNotification}</Btn>
              <Btn attrBtn={{ name: 'basicinfoToast', color: 'info', onClick: (e) => basictoaster(e.target.name) }}>{InfoNotification}</Btn>
              <Btn attrBtn={{ name: 'basicwarningToast', color: 'warning', onClick: (e) => basictoaster(e.target.name) }}>{WarningNotification}</Btn>
              <Btn attrBtn={{ name: 'basicdangerToast', color: 'danger', onClick: (e) => basictoaster(e.target.name) }}>{DangerNotification}</Btn>
            </div>
          </CardBody>
        </Card>
      </Col >
    </Fragment >
  );
};

export default Basic;