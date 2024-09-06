import React, { Fragment, useState } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import Commen from './Commen';

const DefaultTouchSpin = () => {
  const [val, setVal] = useState(40);
  return (
    <Fragment>
      <Col sm='12' md='6'>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'card-title' }}>Default Touchspin</H5>
            <span>
              Add <code>.touchspin</code> class to input to add touchspin input group.
            </span>
          </CardHeader>
          <CardBody>
            <Commen groupText={true} val={val} setVal={setVal} />
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default DefaultTouchSpin;
