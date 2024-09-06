import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardBody } from 'reactstrap';
import { Breadcrumbs, H6, Spinner } from '../../../AbstractElements';
import { LoaderStyle } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import { Data } from './SpinnerData';

const Spinners = (props) => {

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Spinners" parent="Ui Kits" title="Spinners" />
      <Container fluid={true}>
        <Row>
          <Col sm="12">
            <Card>
              <HeaderCard title={LoaderStyle} />
              <CardBody>
                <Row>
                {/* This is just for reference so you cant take it as example of how to use  it */}
                <Col md="3">
                  <H6 attrH6={{ className: 'sub-title mb-0 text-center' }} >{'Loader 1'}</H6>
                  <div className="loader-box">
                    <Spinner attrSpinner={{ className: 'loader-1' }} />
                  </div>
                </Col>
                {/* As there is so many examples, so for repeated code we called it inside loop so we can utilize our code */}
                {Data.map((spinner) =>
                  <Col md="3" key={spinner.id}>
                    <H6 attrH6={{ className: 'sub-title mb-0 text-center' }} >{spinner.heading}</H6>
                    <div className="loader-box">
                      <Spinner attrSpinner={{ className: spinner.spinnerClass }} />
                    </div>
                  </Col>
                )}
                </Row>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Spinners;