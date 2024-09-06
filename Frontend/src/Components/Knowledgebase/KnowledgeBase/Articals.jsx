import { H5, P } from '../../../AbstractElements';
import { ArticalsData } from '../../../Data/KnowledegesBase';
import React, { Fragment } from 'react';
import { Card, CardBody, Col, Media } from 'reactstrap';

const Articals = () => {
  return (
    <Fragment>
      {ArticalsData.map((item, i) => {
        return (
          <Col xl='4' key={item.id} className={`${i === 0 ? 'col-xl-4 box-col-6' : 'col-xl-4 col-sm-6 box-col-6'}`}>
            <Card className='bg-primary'>
              <CardBody>
                <Media className='faq-widgets'>
                  <Media body>
                    <H5>{item.title}</H5>
                    <P>{item.para}</P>
                  </Media>
                  {item.icon}
                </Media>
              </CardBody>
            </Card>
          </Col>
        );
      })}
    </Fragment>
  );
};
export default Articals;
