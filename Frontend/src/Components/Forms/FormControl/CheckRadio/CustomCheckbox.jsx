import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, FormGroup, Label, Input } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { Default, Disabled, Checked, Option, CustomCheckbox, CheckboxStates, InlineCheckbox, SuccessState, BrandState, PrimaryState } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const CustomCheckboxClass = () => {
  return (
    <Fragment>
      <Col md='6'>
        <Card>
          <HeaderCard title={CustomCheckbox} />
          <CardBody>
            <Row>
              <Col sm='12'>
                <H5 attrH5={{ className: 'mb-0' }}>{CustomCheckbox}</H5>
              </Col>
              <Col>
                <FormGroup className='m-t-15 custom-radio-ml'>
                  <div className='checkbox'>
                    <Input id='checkbox1' type='checkbox' />
                    <Label for='checkbox1'>{Default}</Label>
                  </div>
                  <div className='checkbox'>
                    <Input id='checkbox2' type='checkbox' disabled />
                    <Label for='checkbox2'>{Disabled}</Label>
                  </div>
                  <div className='checkbox'>
                    <Input id='checkbox3' type='checkbox' defaultChecked />
                    <Label for='checkbox3'>{Checked}</Label>
                  </div>
                </FormGroup>
              </Col>
              <Col sm='12'>
                <H5 attrH5={{ className: 'mb-0' }}>{CheckboxStates}</H5>
              </Col>
              <Col>
                <FormGroup className='m-t-15 custom-radio-ml'>
                  <div className='checkbox checkbox-primary'>
                    <Input id='checkbox-primary-1' type='checkbox' defaultChecked />
                    <Label for='checkbox-primary-1'>{SuccessState}</Label>
                  </div>
                  <div className='checkbox checkbox-secondary'>
                    <Input id='checkbox-dark' type='checkbox' disabled />
                    <Label for='checkbox-dark'>{BrandState}</Label>
                  </div>
                  <div className='checkbox checkbox-success'>
                    <Input id='checkbox-primary' type='checkbox' defaultChecked />
                    <Label for='checkbox-primary'>{PrimaryState}</Label>
                  </div>
                </FormGroup>
              </Col>
              <Col sm='12'>
                <H5 attrH5={{ className: 'mb-0' }}>{InlineCheckbox}</H5>
              </Col>
              <Col>
                <div className='m-t-15 m-checkbox-inline custom-radio-ml'>
                  <div className='checkbox checkbox-dark'>
                    <Input id='inline-1' type='checkbox' defaultChecked />
                    <Label for='inline-1'>
                      {Option}
                      <span className='digits'> {'1'}</span>
                    </Label>
                  </div>
                  <div className='checkbox checkbox-dark'>
                    <Input id='inline-2' type='checkbox' defaultChecked />
                    <Label for='inline-2'>
                      {Option}
                      <span className='digits'> {'2'}</span>
                    </Label>
                  </div>
                  <div className='checkbox checkbox-dark'>
                    <Input id='inline-3' type='checkbox' defaultChecked />
                    <Label for='inline-3'>
                      {Option}
                      <span className='digits'> {'3'}</span>
                    </Label>
                  </div>
                </div>
              </Col>
            </Row>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default CustomCheckboxClass;
