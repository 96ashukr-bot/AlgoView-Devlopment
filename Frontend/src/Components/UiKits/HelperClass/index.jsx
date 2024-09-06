import React, { Fragment } from 'react';
import { Container, Row, Col } from 'reactstrap';
import MarginCard from './AllMarginCards/Margin';
import PaddingCard from './AllPaddingCards/PaddingsCard';
import PaddingLeftCard from './AllPaddingCards/PaddingLeft';
import PaddingRightCard from './AllPaddingCards/PaddingRight';
import PaddingTopCard from './AllPaddingCards/PaddingTop';
import PaddingBottomCard from './AllPaddingCards/PaddingBottom';
import MarginLeftCard from './AllMarginCards/MarginLeft';
import MarginRightCard from './AllMarginCards/MarginRight';
import MarginTopCard from './AllMarginCards/MarginTop';
import MarginBottomCard from './AllMarginCards/MarginBottom';
import ButtonColorCard from './AllButtonsCards/ButtonColor';
import ButtonOutlineCard from './AllButtonsCards/ButtonOutline';
import AllBorersColorCard from './AllBordersCards/AllBordersColor/index';
import BorderRadiusCard from './AllBordersCards/BorderRadius';
import BorderWidthCard from './AllBordersCards/BorderWidth';
import FontSizeCard from './AllFontsCards/FontSize';
import FontWeightCard from './AllFontsCards/FontWeight';
import FontStyleCard from './AllFontsCards/FontStyle';
import BackgroundColorCard from './BackgroundColor';
import ImageSizesCard from './ImageSizes';
import FloatCard from './Float';
import OverFlowCard from './Overflow';
import PositionCard from './Position';
import TextColorCard from './TextColor';
import VerticalAlignCard from './VerticalAlign';
import BadgeColorCard from './BadgeColor';
import { Breadcrumbs } from '../../../AbstractElements';

const HelperClasses = () => {

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Helper Classes" parent="Ui Kits" title="Helper Classes" />
      <Container fluid={true}>
        <Row>
          <PaddingCard />
          <MarginCard />
          <PaddingLeftCard />
          <PaddingRightCard />
          <PaddingTopCard />
          <PaddingBottomCard />
          <MarginLeftCard />
          <MarginRightCard />
          <MarginTopCard />
          <MarginBottomCard />
          <VerticalAlignCard />
          <ImageSizesCard />
          <TextColorCard />
          <BadgeColorCard />
          <BackgroundColorCard />
          <ButtonColorCard />
          <Col xl="6">
            <BorderRadiusCard />
            <FontWeightCard />
            <FontStyleCard />
            <FloatCard />
            <OverFlowCard />
          </Col>
          <FontSizeCard />
          <AllBorersColorCard />
          <Col xl="6">
            <BorderWidthCard />
            <PositionCard />
            <ButtonOutlineCard />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default HelperClasses;