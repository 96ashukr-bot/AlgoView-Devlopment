import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import ClickAndDrag from './ClickDrag';
import AlwaysVisibleScroll from './AlwaysVisibleScroll';
import BothSideScroll from './BothSideScroll';
import HorizontalScroll from './HorizontalScroll';
import SmallSizeScroll from './SmallSizeScroll';
import VerticalScroll from './VerticalScroll';

const Scrollable = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Scrollable' parent='Bonus Ui' title='Scrollable' />
      <Container fluid={true}>
        <Row>
          <ClickAndDrag />
          <SmallSizeScroll />
          <BothSideScroll />
          <HorizontalScroll />
          <AlwaysVisibleScroll />
          <VerticalScroll />
        </Row>
      </Container>
    </Fragment>
  );
};

export default Scrollable;
