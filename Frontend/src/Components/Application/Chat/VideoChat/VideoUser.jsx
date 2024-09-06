import React, { Fragment } from 'react';
import { Image } from '../../../../AbstractElements';

const VideoUser = () => {
  var images = require.context('../../../../assets/images', true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };
  return (
    <Fragment>
      <div className='media'>
        <Image
          attrImage={{
            src: `${dynamicImage('user/12.png')}`,
            className: 'rounded-circle user-image',
            alt: '',
          }}
        />
        <div className='about'>
          <div className='name f-w-600'>{'Johan Deo'}</div>
          <div className='status'>{'Out is my favorite'}</div>
        </div>
      </div>
    </Fragment>
  );
};

export default VideoUser;
