import React, { Fragment } from 'react';
import { Card, CardBody, Col, Media, Row } from 'reactstrap';
import { H6, P } from '../../AbstractElements';
import { ArticeVideoData3 } from '../../Data/FAQ';

const ArticeVideo3 = () => {
  return (
    <Fragment>
      <Col xl='4' className='video-sec'>
        <Row>
          {ArticeVideoData3.map((item, i) => {
            return (
              <Col xl='12' md='6' key={i}>
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
export default ArticeVideo3;
