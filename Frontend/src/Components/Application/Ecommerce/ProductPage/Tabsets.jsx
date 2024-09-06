import React, { Fragment, useState } from 'react';
import { Card, Row, Col, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { Febric, Video, Details, Brand } from '../../../../Constant';

const Tabset = () => {
  const [activeTab, setActiveTab] = useState('1');
  return (
    <Fragment>
      <Card>
        <div className='product-page-main'>
          <Row className='m-0'>
            <Col sm='12'>
              <Nav tabs className='border-tab nav-primary mb-0 '>
                <NavItem id='myTab' role='tablist'>
                  <NavLink href='#' className={activeTab === '1' ? 'active' : ''} onClick={() => setActiveTab('1')}>
                    {Febric}
                  </NavLink>
                  <div className='material-border'></div>
                </NavItem>
                <NavItem id='myTab' role='tablist'>
                  <NavLink href='#' className={activeTab === '2' ? 'active' : ''} onClick={() => setActiveTab('2')}>
                    {Video}
                  </NavLink>
                  <div className='material-border'></div>
                </NavItem>
                <NavItem id='myTab' role='tablist'>
                  <NavLink href='#' className={activeTab === '3' ? 'active' : ''} onClick={() => setActiveTab('3')}>
                    {Details}
                  </NavLink>
                  <div className='material-border'></div>
                </NavItem>
                <NavItem id='myTab' role='tablist'>
                  <NavLink href='#' className={activeTab === '4' ? 'active' : ''} onClick={() => setActiveTab('4')}>
                    {Brand}
                  </NavLink>
                  <div className='material-border'></div>
                </NavItem>
              </Nav>
              <TabContent activeTab={activeTab}>
                <TabPane tabId='1'>
                  <P attrPara={{ className: 'mb-0 m-t-20' }}>
                    {' '}
                    {
                      'Button concelead zip front fastening strech micro modal straight-leg drawstring waste. Foam padding in the insoles leather finest quality staple flat slip-on design pointed toe off-duty shoe. Best seller signature waist cut pockets cotton-mix navy blue tailoring elegant cashmere.  Faux real sexy split up the back pockets cut out detail on the front strappy brown paisley print.  Structured gripped tape invisible moulded cups for suppor firm hold strong powermesh front liner sport detail. '
                    }
                  </P>
                  <P attrPara={{ className: 'mb-0 m-t-20' }}>
                    {
                      'Flattering high rise easy care flared fit - cut straight leg that flares at the ankle comfy tight. Rear jetted pocket wide-leg trousers button fastening brown details slim straight white. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Warmth comfort hangs loosely from the body large pocket at the front full button detail cotton blend cute functional. Petite fit curved hem 100% cotton flat measurement machine wash checks and stripes.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='2'>
                  <P attrPara={{ className: 'mb-0 m-t-20' }}>
                    {
                      'Printed lining patch pockets jersey blazer built in pocket square wool casual quilted jacket without hood azure. Cutting edge crops stone transparent alterated night out gloss lush blimey satin smooth. Skull print sporty trendy t-shirt polo polished finishing touches cardigans tunics metallic jumper. Slimming removable contrast straps black waist band ultra-feminine floral print versatility of wear sun-soaked. Embroidered logo chest pocket locker loop button-flap breast pockets fastening jetted.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='3'>
                  <P attrPara={{ className: 'mb-0 m-t-20' }}>
                    {' '}
                    {
                      'Bodycon skirts bright primary colours punchy palette pleated cheerleader vibe stripe trims. Structured chic panels power party flattering ultimate trim back pencil silhouette perfect look. Tops shift shape rich fabric relaxed fitting size true black gold zip virgin wool. Invisible pockets lightweight non-crease concealed zip polyester cool hand wash crochet lace. Bow detail metallic eyelets leather lining luxurious finish classic courts formal slingback square toe contrasting cap.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='4'>
                  <P attrPara={{ className: 'mb-0 m-t-20' }}>
                    {
                      'Machine wash cold slim fit premium stretch selvedge denim comfortable low waist. A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Western-inspired suede jacket denim blue metallic button fastening summer white pure hue subtle distressed casual appeal. Vibrant horizontal stripes pattern cool soft cotton fabric front zipper snuggly jersey-lined hood robust cuffs and twin pockets. Monochrome textures casual daily polo neck knitted floral effortless short sleeve.'
                    }
                  </P>
                </TabPane>
              </TabContent>
            </Col>
          </Row>
        </div>
      </Card>
    </Fragment>
  );
};

export default Tabset;
