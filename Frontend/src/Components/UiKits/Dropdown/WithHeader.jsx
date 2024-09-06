import React from 'react';
import { Card, CardBody, CardHeader, Col, Dropdown, DropdownItem, DropdownMenu } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { AnotherLink, DropdownButton, DropdownHeader, DropdownWithHeader } from '../../../Constant';

const WithHeader = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{DropdownWithHeader}</H5><span>{'Use a class'} <code>{'.dropdown-header'}</code></span>
        </CardHeader>
        <CardBody>
          <div className="dropdown-basic">
            <Dropdown>
              <Btn attrBtn={{ color: 'primary', className: 'dropbtn' }}>{DropdownButton} <span><i className="icofont icofont-arrow-down"></i></span></Btn>
              <DropdownMenu className="dropdown-content">
                <DropdownItem header>{DropdownHeader}</DropdownItem>
                <DropdownItem href="#">{'Link 1'}</DropdownItem>
                <DropdownItem href="#">{'Link 2'}</DropdownItem>
                <DropdownItem header>{DropdownHeader}</DropdownItem>
                <DropdownItem href="#">{AnotherLink}</DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithHeader;