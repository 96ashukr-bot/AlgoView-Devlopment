import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import SizingCard from './SizingCard';
import StatusIndicatorCard from './StatusIndicatorCard';
import ShapeCard from './ShapeCard';
import InitialsCard from './InitialsCard';
import GroupCard from './GroupCard';
import { Breadcrumbs } from '../../../AbstractElements';

const Avatars = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Avatars" parent="Ui Kits" title="Avatars" />
      <Container fluid={true}>
        <div className="user-profile">
          <Row>
            <SizingCard />
            <StatusIndicatorCard />
            <InitialsCard />
            <ShapeCard />
            <GroupCard />
          </Row>
        </div>
      </Container>
    </Fragment>
  );
};

export default Avatars;