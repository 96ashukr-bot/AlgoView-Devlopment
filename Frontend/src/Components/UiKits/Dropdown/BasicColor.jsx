import React from 'react';
import { Card, CardBody, Col, Dropdown, DropdownItem, DropdownMenu } from 'reactstrap';
import { Btn } from '../../../AbstractElements';
import { Action, AnotherAction, BasicColorDropdown, SomethingElseHere } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import { BasicColorData } from '../../Common/Data/Ui-kits';
import CommonDropDown from './Common/CommonDropDown';

const BasicColor = () => {


  return (
    <Col sm="12" xl="12">
      <Card>
        <HeaderCard title={BasicColorDropdown} />
        <CardBody>
          <div className="dropdown-basic">
            <Dropdown>
              <div className="btn-group mb-0">
                <Btn attrBtn={{ color: 'primary', className: 'dropbtn' }} >Action <span><i className="icofont icofont-arrow-down"></i></span></Btn>
                <DropdownMenu className="dropdown-content">
                  <DropdownItem href="#">{Action}</DropdownItem>
                  <DropdownItem href="#">{AnotherAction}</DropdownItem>
                  <DropdownItem href="#">{SomethingElseHere}</DropdownItem>
                  <DropdownItem divider />
                  <DropdownItem href="#">{'Separated Link'}</DropdownItem>
                </DropdownMenu>
              </div>
            </Dropdown>
            {BasicColorData.map((items) =>
              <CommonDropDown key={items.id} item={items} />
            )}
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default BasicColor;