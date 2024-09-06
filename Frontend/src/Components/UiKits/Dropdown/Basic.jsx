import React from 'react';
import { Card, CardBody, Col, Dropdown, DropdownItem, DropdownMenu } from 'reactstrap';
import { Btn } from '../../../AbstractElements';
import { Action, AnotherAction, BasicDropdown, DropdownButton, SomethingElseHere } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const Basic = () => {
  return (
    <Col sm="12" xl="12">
      <Card>
        <HeaderCard title={BasicDropdown} />
        <CardBody>
          <div className="dropdown-basic">
            <Dropdown className="dropdown">
              <Btn attrBtn={{ color: 'primary', className: 'dropbtn' }} >{DropdownButton} <span><i className="icofont icofont-arrow-down"></i></span></Btn>
              <DropdownMenu className="dropdown-content">
                <DropdownItem href="#">{Action}</DropdownItem>
                <DropdownItem href="#">{AnotherAction}</DropdownItem>
                <DropdownItem href="#">{SomethingElseHere}</DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Basic;