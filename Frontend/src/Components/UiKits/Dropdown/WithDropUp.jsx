import React from 'react';
import { Card, CardBody, CardHeader, Col, Dropdown, DropdownItem, DropdownMenu } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { DropdownButton, DropdownWithDropUp } from '../../../Constant';

const WithDropUp = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{DropdownWithDropUp}</H5><span>{'Use a class'} <code>{'.drop-up'}</code></span>
        </CardHeader>
        <CardBody>
          <div className="dropup-basic">
            <Dropdown className="dropup">
              <Btn attrBtn={{ color: 'primary', className: 'dropbtn' }}  >{DropdownButton} <span><i className="icofont icofont-arrow-up"></i></span></Btn>
              <DropdownMenu className="dropup-content dropdown-content">
                <DropdownItem href="#">{'Link 1'}</DropdownItem>
                <DropdownItem href="#">{'Link 2'}</DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithDropUp;