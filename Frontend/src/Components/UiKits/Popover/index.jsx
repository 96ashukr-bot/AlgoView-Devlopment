import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import Basic from './Basic';
import Directions from './Direction';
import HtmlContents from './HtmlConten';
import Offset from './Offset';

const PopOvers = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Popover" parent="Ui Kits" title="Popover" />
      <Container fluid={true}>
        <Row className="popover-main">
          <Basic />
          <Directions />
          <HtmlContents />
          <Offset />
        </Row>
      </Container>
    </Fragment>
  );
};
export default PopOvers;