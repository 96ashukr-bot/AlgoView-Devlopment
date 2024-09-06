import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import { Examples } from '../../../Constant';
import LargeShadows from './Large';
import NoShadows from './NoShadow';
import RegularShadows from './Regular';
import SmallShadows from './Small';

const Shadow = (props) => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Shadow" parent="Ui Kits" title="Box Shadow" />
      <Container fluid={true}>
        <Row>
          <Col sm="12">
            <Card className="box-shadow-title">
              <CardHeader>
                <h5>{Examples}</h5><span>{'While shadows on components are disabled by default in Bootstrap and can be enabled via'} <code>{'$enable-shadows'}</code>, {'you can also quickly add or remove a shadow with our'} <code>{'box-shadow'}</code> {'utility classes. Includes support for'} <code>{'.shadow-none'}</code> {'and three default sizes (which have associated variables to match).'}</span>
              </CardHeader>
              <CardBody>
                <Row>
                  <LargeShadows />
                  <RegularShadows />
                  <SmallShadows />
                  <NoShadows />
                </Row>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Shadow;