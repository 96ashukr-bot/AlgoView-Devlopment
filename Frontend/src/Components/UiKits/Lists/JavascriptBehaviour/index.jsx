import React, { useState } from 'react';
import { Card, CardBody, Col, Row, TabContent, TabPane } from 'reactstrap';
import { LI, UL } from '../../../../AbstractElements';
import { Hometxt, JavaScriptBehavior, Messages, Profile, Settings } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const JavascriptBase = () => {
  const [activeTab, setActiveTab] = useState('1');

  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={JavaScriptBehavior} />
        <CardBody>
          <Row>
            <Col sm='4 tab-javascript'>
              <UL attrUL={{ className: 'simple-list nav-primary nav-pills' }}>
                <LI attrLI={{ href: '#javascript', className: `p-1 border-0 list-group-item-action ${activeTab === '1' && 'active'}`, onClick: () => setActiveTab('1') }}>{Hometxt}</LI>
              </UL>
              <UL>
                <LI attrLI={{ href: '#javascript', className: `p-1 border-0 list-group-item-action ${activeTab === '2' && 'active'}`, onClick: () => setActiveTab('2') }}>{Profile}</LI>
              </UL>
              <UL>
                <LI attrLI={{ href: '#javascript', className: `p-1 border-0 list-group-item-action ${activeTab === '3' && 'active'}`, onClick: () => setActiveTab('3') }}>{Messages}</LI>
              </UL>
              <UL>
                <LI attrLI={{ href: '#javascript', className: `p-1 border-0 list-group-item-action ${activeTab === '4' && 'active'}`, onClick: () => setActiveTab('4') }}>{Settings}</LI>
              </UL>
            </Col>
            <Col sm='8'>
              <TabContent activeTab={activeTab}>
                <TabPane tabId='1' className='fade show'>
                  {
                    '1. Slimming removable contrast straps black waist band ultra-feminine floral print versatility of wear sun-soaked. Stiletto courts special occasion glossy embellished upper peep toe high heel twiste pretty lace detailing sultry finish. Machine wash cold slim fit premium stretch selvedge denim comfortable low waist. Faux real sexy split up the back pockets cut out detail on the front strappy brown paisley print. Flattering high rise easy care flared fit - cut straight leg that flares at the ankle comfy tight.'
                  }
                </TabPane>
                <TabPane tabId='2' className='fade show'>
                  {
                    '2. Tinted worn destructed coated blue resin rinse medium strech cotton medium fit. Micro minis floor-sweeping maxi skirts matchy-matchy decorative floral embroidery nature motifs. Bow detail metallic eyelets leather lining luxurious finish classic courts formal slingback square toe contrasting cap. Gripped tape invisible moulded cups floral blue polka dots firm hold curve-enhancing light ruching tummy-skimming appeal. Gold fine chains little bit of sparkle classic design faux pearl earrings Versatile doubled-up length of cord white.'
                  }
                </TabPane>
                <TabPane tabId='3' className='fade show'>
                  {
                    '3. Strech lining hemline above knee burgundy satin finish concealed zip small buttons rayon. Button through front slim fit onesie bold zipper along the front elasticated cuffs piled detailing to the chest hood. Western-inspired suede jacket denim blue metallic button fastening summer white pure hue subtle distressed casual appeal. Leather asymmetric zip fastening wide lapels snap button zipped cuffs softer texture open asymmetric neckline tab sleeves. Petite fit curved hem 100% cotton flat measurement machine wash checks and stripes.'
                  }
                </TabPane>
                <TabPane tabId='4' className='fade show'>
                  {
                    '4. Pocket detail to sides jacquard fabric fully lined notch lapel three-button cuffs contrast stitching classic colar. Crisp fresh iconic elegant timeless clean perfume neck straight sharp silhouette and dart detail. Print perfect funky inspired pull ring side pockets pink black and orange print thick fabric skirt. Pop top sporty stripe trims mesh inserts denim turtle neck casual white cotton button silver. Rock wolf double washed heavy cotton mix made in white iron do not wash stamp.'
                  }
                </TabPane>
              </TabContent>
            </Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default JavascriptBase;
