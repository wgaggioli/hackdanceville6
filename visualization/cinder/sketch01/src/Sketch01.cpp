#include "cinder/app/AppNative.h"
#include "cinder/app/RendererGl.h"
#include "cinder/gl/Shader.h"
#include "cinder/gl/Batch.h"
#include "cinder/gl/VboMesh.h"
#include "cinder/ImageIo.h"
#include "cinder/Triangulate.h"
#include "cinder/Utilities.h"

#include "cinder/audio/Context.h"
#include "cinder/audio/SamplePlayerNode.h"
#include "cinder/audio/MonitorNode.h"
#include "cinder/audio/GainNode.h"
#include "cinder/audio/FilterNode.h"
#include "cinder/audio/Utilities.h"

using namespace ci;
using namespace ci::app;

class Sketch01App : public AppNative {
public:
	virtual void	setup() override;
	virtual void	resize() override;
	virtual void	update() override;
	virtual void	draw() override;
	virtual void	fileDrop( FileDropEvent event ) override;
	virtual void	keyDown( KeyEvent event ) override;
	virtual void	mouseMove( MouseEvent event ) override;
	virtual void	prepareSettings( ci::app::AppBasic::Settings *settings ) override;

	void drawOutline( size_t lineWidth );

	CameraPersp			mCam;
	gl::BatchRef		mBatch;
	gl::TextureRef		mDepthTexture;
	Channel32f			mChannel;
	gl::GlslProgRef		mTestShader;
	audio::FilePlayerNodeRef		mFilePlayerNode;
	audio::MonitorNodeRef			mMonitorNode1;
	audio::MonitorNodeRef			mMonitorNode2;
	audio::GainNodeRef				mGainNode;
	audio::FilterLowPassNodeRef		mLowpassNode;
	audio::FilterHighPassNodeRef	mHighpassNode;
};

void Sketch01App::prepareSettings( Settings* settings )
{
	settings->prepareWindow( Window::Format().size( 960, 720 ).title( "Sketch01" ) );
	//settings->setFrameRate( 60.0f );
}

void Sketch01App::setup()
{
	mChannel = Channel32f( loadImage( loadAsset( "depth.png" ) ) );
	mDepthTexture = gl::Texture::create( mChannel );

	mFilePlayerNode = audio::Context::master()->makeNode( new audio::FilePlayerNode() );
	mGainNode = audio::Context::master()->makeNode( new audio::GainNode( 0.5f ) );
	//mFilePlayerNode >> mGainNode >> audio::Context::master()->getOutput();
	mGainNode >> audio::Context::master()->getOutput();

	mMonitorNode1 = audio::Context::master()->makeNode( new audio::MonitorNode() );
	mMonitorNode2 = audio::Context::master()->makeNode( new audio::MonitorNode() );
	mLowpassNode = audio::Context::master()->makeNode( new audio::FilterLowPassNode() );
	mHighpassNode = audio::Context::master()->makeNode( new audio::FilterHighPassNode() );

	mLowpassNode >> mMonitorNode1;
	mHighpassNode >> mMonitorNode2;
}

void Sketch01App::fileDrop( FileDropEvent event )
{
	fs::path filePath = event.getFile( 0 );
	getWindow()->setTitle( filePath.filename().string() );

	//audio::Context::master()->disable();
	audio::SourceFileRef sourceFile = audio::load( loadFile( filePath ) );

	mFilePlayerNode->setSourceFile( sourceFile );
	mFilePlayerNode->setLoopEnabled();
	mFilePlayerNode >> mGainNode;

	mFilePlayerNode >> mLowpassNode;
	mFilePlayerNode >> mHighpassNode;

	audio::Context::master()->enable();
	mFilePlayerNode->start();

	mLowpassNode->enable();
	//mLowpassNode->setMode();
}

void Sketch01App::resize()
{
}

void Sketch01App::update()
{

}

void Sketch01App::draw()
{
	gl::disableDepthWrite();
	gl::disableDepthRead();

	gl::clear( Color::gray( 1.0f ) );
	gl::color( Color::white() );
	gl::draw( mDepthTexture, this->getWindowBounds() );
	
	//gl::enableDepthWrite();
	//gl::enableDepthRead();
	
	gl::ScopedAlphaBlend( false );

	float radius = 300;
	ivec2 center = getWindowCenter();
	if( mMonitorNode1->isEnabled() ) {
		gl::color( ColorA( 1.0, 0.0, 0.0, 0.5 ) );
		ci::gl::drawSolidCircle( center + ivec2( 0, 0 ), radius * mMonitorNode1->getVolume() );
	}

	if( mMonitorNode2->isEnabled() ) {
		gl::color( ColorA( 0.0, 0.0, 1.0, 0.5 ) );
		ci::gl::drawSolidCircle( center + ivec2( 0, 0 ), radius * mMonitorNode2->getVolume() );
	}
}

void Sketch01App::keyDown( KeyEvent event )
{
	if( event.getCode() == KeyEvent::KEY_SPACE ) {
		if( mFilePlayerNode->isEnabled() ) {
			mFilePlayerNode->stop();
		}
		else {
			mFilePlayerNode->start();
		}
	}
	else if( event.getCode() == KeyEvent::KEY_UP ) {
		if( mGainNode->isEnabled() ) {
			mGainNode->setValue( mGainNode->getValue() + 0.1f );
		}
	}
	else if( event.getCode() == KeyEvent::KEY_DOWN ) {
		if( mGainNode->isEnabled() ) {
			mGainNode->setValue( mGainNode->getValue() - 0.1f );
		}
	}
}

void Sketch01App::mouseMove( MouseEvent event )
{
	if( !getWindowBounds().contains( event.getPos() ) )
		return;
}

CINDER_APP_NATIVE( Sketch01App, RendererGl )
