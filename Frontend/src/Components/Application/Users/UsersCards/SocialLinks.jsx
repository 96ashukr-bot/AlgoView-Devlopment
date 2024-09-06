import React from 'react';
import { LI, UL } from '../../../../AbstractElements';
const SocialLinks = () => {
  return (
    <UL attrUL={{horizontal:true, className: 'd-flex justify-content-center card-social' }}>
      <LI>
        <a href='https://www.facebook.com/' target='_blank' rel="noreferrer">
          <i className='fa fa-facebook' />
        </a>
      </LI>
      <LI>
        <a href='https://accounts.google.com/' target='_blank' rel="noreferrer">
          <i className='fa fa-google-plus' />
        </a>
      </LI>
      <LI>
        <a href='https://twitter.com/' target='_blank' rel="noreferrer">
          <i className='fa fa-twitter' />
        </a>
      </LI>
      <LI>
        <a href='https://www.instagram.com/' target='_blank' rel="noreferrer">
          <i className='fa fa-instagram' />
        </a>
      </LI>
      <LI>
        <a href='https://rss.app/' target='_blank' rel="noreferrer">
          <i className='fa fa-rss' />
        </a>
      </LI>
    </UL>
  );
};

export default SocialLinks;
