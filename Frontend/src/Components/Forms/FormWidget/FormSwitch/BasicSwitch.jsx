import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Input, Label, Media } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { BasicSwitchData } from '../../../../Data/FormWidgets';

const BasicSwitch = () => {
  return (
    <Fragment>
      <Col sm='12' xl='6' lg='12' md='6'>
        <Card>
          <CardHeader>
            <H5>Basic Switch</H5>
          </CardHeader>
          <CardBody className='row switch-showcase height-equal'>
            <Col sm='12'>
              {BasicSwitchData.map((item) => {
                return (
                  <Media key={item.id}>
                    <Label className='col-form-label m-r-10'>{item.title}</Label>
                    <Media body className={item.mediaclass}>
                      <Label className='switch'>
                        <Input type='checkbox' disabled={item.disabled} />
                        <span className='switch-state'></span>
                      </Label>
                    </Media>
                  </Media>
                );
              })}
            </Col>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default BasicSwitch;
