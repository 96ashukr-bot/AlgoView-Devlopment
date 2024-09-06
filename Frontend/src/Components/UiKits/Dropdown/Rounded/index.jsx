import React from 'react';
import { Button, ButtonGroup, Card, CardBody, CardHeader, Col, Dropdown, DropdownItem, DropdownMenu } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { RoundedDropdown } from '../../../../Constant';
import CommonDropDown from '../Common/CommonDropDown';
import { RoundedData } from '../../../Common/Data/Ui-kits';

const Rounded = () => {


  return (
    <Col sm="12" xl="12">
      <Card>
        <CardHeader>
          <H5>{RoundedDropdown}</H5>
        </CardHeader>
        <CardBody>
          <div className="dropdown-basic">
            <Dropdown>
              <ButtonGroup className="mb-0">
                <Button className="dropbtn btn-round rounded-pill" color={'primary'}>Primary button<span><i className="icofont icofont-arrow-down"></i></span></Button>
                <DropdownMenu className="dropdown-content">
                  <DropdownItem href="#">Action</DropdownItem>
                  <DropdownItem href="#">Another Action</DropdownItem>
                  <DropdownItem href="#">Something Else Here</DropdownItem>
                  <DropdownItem href="#">Separated Link</DropdownItem>
                </DropdownMenu>
              </ButtonGroup>
            </Dropdown>
            {RoundedData.map((items) =>
              <CommonDropDown key={items.id} item={items} />
            )}
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Rounded;