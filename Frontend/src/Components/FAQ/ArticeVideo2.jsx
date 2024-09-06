import React, { Fragment } from 'react';
import { Card, CardBody, Col, Media, Row } from 'reactstrap';
import { H6, P } from '../../AbstractElements';
import { ArticeVideoData2 } from '../../Data/FAQ';

const ArticeVideo2 = () => {
  return (
    <Fragment>
      <Col xl='4' md='6'>
        <Row>
          {ArticeVideoData2.map((item, i) => {
            return (
              <Col sm='12' key={i}>
                <Card>
                  <CardBody>
                    <Media>
                      {item.IconClass}
                      <Media body>
                        <H6 attrH6={{ className: 'f-w-600' }}>{item.title}</H6>
                        <P>{item.discription}</P>
                      </Media>
                    </Media>
                  </CardBody>
                </Card>
              </Col>
            );
          })}
        </Row>
      </Col>
    </Fragment>
  );
};
export default ArticeVideo2;
