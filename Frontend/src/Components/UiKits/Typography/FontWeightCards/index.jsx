import React, { Fragment } from 'react';
import { Col } from 'reactstrap';
import Bold700Card from './Bold700Card';
import Bold900Card from './Bold900Card';
import Normal400Card from './Normal400Card';
import Normal600Card from './Normal600card';
import Thin100Card from './Thin100';
import Thin300Card from './Thin300Card';

const FontWeightCards= () =>{
return(
  <Fragment>
    <Col sm="12" xl="4">
      <Thin100Card />
    </Col>
    <Col sm="12" xl="4">
      <Thin300Card />
    </Col>
    <Col sm="12" xl="4">
      <Normal400Card />
    </Col>
    <Col sm="12" xl="4">
      <Normal600Card />
    </Col>

    <Col sm="12" xl="4">
      <Bold700Card />
    </Col>

    <Col sm="12" xl="4">
      <Bold900Card />
    </Col>
  </Fragment>
);
};

export default FontWeightCards;