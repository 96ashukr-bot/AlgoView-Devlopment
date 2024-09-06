import React from 'react';
import { Card, CardBody, CardHeader, Col, Dropdown, DropdownItem, DropdownMenu } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { Active, Disabled, DropdownButton, DropdownWithDisable, Normal } from '../../../Constant';

const WithDisable = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{DropdownWithDisable}</H5><span>{'Use a class'} <code>{'.dropdown-divider'}</code></span>
        </CardHeader>
        <CardBody>
          <div className="dropup-basic">
            <Dropdown className="dropup">
              <Btn attrBtn={{ color: 'primary', className: 'dropbtn' }}>{DropdownButton} <span><i className="icofont icofont-arrow-up"></i></span></Btn>
              <DropdownMenu className="dropup-content dropdown-content">
                <DropdownItem href="#">{Normal}</DropdownItem>
                <DropdownItem href="#" active>{Active}</DropdownItem>
                <DropdownItem href="#" disabled>{Disabled}</DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithDisable;