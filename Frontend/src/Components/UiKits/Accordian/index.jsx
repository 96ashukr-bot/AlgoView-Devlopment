import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import BasicAccordions from './Basic';
import AllClose from './AllClose';
import PrimaryColorAccordian from './PrimaryColorAccordian';
import SecondaryColorAccordian from './SecondaryColorAccordian';
import WithIcon from './WithIcon';
import WithOperand from './WithOperand';
import { Breadcrumbs } from '../../../AbstractElements';

const Accordian = (props) => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Accordian" parent="Ui Kits" title="Accordian" />
      <Container fluid={true}>
        <Row>
          <BasicAccordions />
          <AllClose />
          <PrimaryColorAccordian />
          <SecondaryColorAccordian />
          <WithIcon />
          <WithOperand />
        </Row>
      </Container>
    </Fragment>
  );
};
export default Accordian;