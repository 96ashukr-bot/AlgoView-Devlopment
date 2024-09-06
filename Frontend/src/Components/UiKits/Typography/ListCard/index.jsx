import React from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5, H6, LI, OL, UL } from '../../../../AbstractElements';
import { FontawesomeList, ICOIconList, ListingTypography, OrderList, ThemfyList, UnorderList } from '../../../../Constant';

const ListCard = () => {
  let ULtypography = ['Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet', 'Lorem ipsum dolor sit amet'];
  let OLtypography = ['<dt>Lorem ipsum dolor sit amet</dt><dd>- ipsum dolor sit amet</dd>', `<dt>Lorem ipsum dolor sit amet</dt><dd>- ipsum dolor sit amet</dd>`, `<dt>Lorem ipsum dolor sit amet</dt><dd>- ipsum dolor sit amet</dd>`, `<dt>Lorem ipsum dolor sit amet</dt><dd>- ipsum dolor sit amet</dd>`, `<dt>Lorem ipsum dolor sit amet</dt><dd>- ipsum dolor sit amet</dd>`];
  let Fontawesomelist = ['<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-angle-double-right txt-primary me-2"></i>Lorem ipsum dolor sit amet'];
  let Iconlist = ['<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet', '<i class="fa fa-caret-right txt-secondary me-2"></i>Lorem ipsum dolor sit amet'];
  let Themfylist = ['<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet', '<i class="icofont icofont-ui-rate-add txt-success me-2"></i>Lorem ipsum dolor sit amet'];;

  return (
    <Col sm="12 listing">
      <Card>
        <CardHeader>
          <H5>{ListingTypography}</H5>
        </CardHeader>
        <CardBody>
          <Row>
            <Col sm="12" xl="4">
              <H6 attrH6={{ className: 'sub-title' }}>{UnorderList}</H6>
              <UL attrUL={{ as: 'ul', className: 'simple-list' }} listItem={ULtypography} />
            </Col>

            <Col sm="12" xl="4">
              <H6 attrH6={{ className: 'sub-title' }}>{OrderList}</H6>
              <OL attrOL={{ className: 'd-block simple-list' }}>
                <LI val='Lorem ipsum dolor sit amet' />
                <LI val='Lorem ipsum dolor sit amet' />
                <LI val='Lorem ipsum dolor sit amet' />
                <LI>
                  <OL attrOL={{ className: 'd-block simple-list' }}>
                    <LI val='Lorem ipsum dolor sit amet' />
                    <LI val='Lorem ipsum dolor sit amet' />
                    <LI val='Lorem ipsum dolor sit amet' />
                    <LI val='Lorem ipsum dolor sit amet' />
                    <LI val='Lorem ipsum dolor sit amet' />
                  </OL>
                </LI>
                <LI val='Lorem ipsum dolor sit amet' />
                <LI val='Lorem ipsum dolor sit amet' />
              </OL>
            </Col>

            <Col sm="12" xl="4">
              <H6 attrH6={{ className: 'sub-title' }}>{OrderList}</H6>
              <UL attrUL={{ as: 'dl', className: 'simple-list' }} listItem={OLtypography} />
            </Col>

            <Col sm="12" xl="4">
              <H6 attrH6={{ className: 'sub-title' }}>{FontawesomeList}</H6>
              <UL attrUL={{ as: 'ul', className: 'simple-list' }} listItem={Fontawesomelist} />
            </Col>

            <Col sm="12" xl="4">
              <H6 attrH6={{ className: 'sub-title' }}>{ICOIconList}</H6>
              <UL attrUL={{ as: 'ul', className: 'simple-list' }} listItem={Iconlist} />
            </Col>

            <Col sm="12" xl="4">
              <H6 attrH6={{ className: 'sub-title' }}>{ThemfyList}</H6>
              <UL attrUL={{ as: 'ul', className: 'simple-list' }} listItem={Themfylist} />
            </Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default ListCard;