import { H4, Image, LI, P, UL } from '../../../AbstractElements';
import React, { Fragment } from 'react';
import { Card } from 'reactstrap';

const BlogDetails = () => {
  return (
    <Fragment>
      <div className='blog-box blog-details'>
        <Card>
          <Image attrImage={{ className: 'img-fluid w-100', src: `${require('../../../assets/images/faq/learning-1.png')}`, alt: 'blog-main' }} />
        </Card>
        <div className='blog-details'>
          <UL attrUL={{ className: 'blog-social flex-row' }}>
            <LI attrLI={{ className: 'digits' }}>{'25 July 2022'}</LI>
            <LI>
              <i className='icofont icofont-user'></i>
              {'Mark'} <span>{'Jecno'} </span>
            </LI>
            <LI attrLI={{ className: 'digits' }}>
              <i className='icofont icofont-thumbs-up'></i>
              {'02'}
              <span>{'Hits'}</span>
            </LI>
            <LI attrLI={{ className: 'digits' }}>
              <i className='icofont icofont-ui-chat'></i>
              {'598 Comments'}
            </LI>
          </UL>
          <H4>{'Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. '}</H4>
          <div className='single-blog-content-top'>
            <P>
              {
                'Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Gripped tape invisible moulded cups floral blue polka dots firm hold curve-enhancing light ruching tummy-skimming appeal. Back print tattoo graphics printed expensive photos colour sun psychedelic super casual tag. Faux real sexy split up the back pockets cut out detail on the front strappy brown paisley print. Leather asymmetric zip fastening wide lapels snap button zipped cuffs softer texture open asymmetric neckline tab sleeves.'
              }
            </P>
            <P>
              {
                "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. Many desktop publishing packages and web page editors now use Lorem Ipsum as their default model text, and a search for 'lorem ipsum' will uncover many web sites still in their infancy. Various versions have evolved over the years, sometimes by accident, sometimes on purpose (injected humour and the like"
              }
            </P>
          </div>
        </div>
      </div>
    </Fragment>
  );
};

export default BlogDetails;
