const del = require('del');
const gulp = require('gulp');
const merge = require('merge-stream');
const rename = require('gulp-rename');
const replace = require('gulp-replace');
const zip = require('gulp-zip');
const pages = require('gh-pages');
const sync = require('browser-sync').create();
const cp=require('child_process')
const newer = require('gulp-newer');
const through = require('through2');
const vinylFile = require('vinyl-file')
var readline = require('readline');
var fs = require("fs");
var mustache = require("gulp-mustache");
const debug = require('gulp-debug');
stream=require('browser-sync').stream;

const make_cp_pipeline=function(process,srcPattern,destPattern,script_props){
    const pipelines=[]
    
    script_props.forEach(function(element){
	const plot_scripts = gulp.src(
	    [element.script]
	).pipe(
	    newer(
		element.dest
	    )
	).pipe(makePictures(
	    process,srcPattern,destPattern
	)).pipe(rename( (path) => {
	path.dirname = 'pictures'
	}));
	pipelines.push(plot_scripts)
    })

    return merge(pipelines)
}

gulp.task('prepare', (done) => {

    const shower = gulp.src([
            '**',
            '!movies/**',
            '!docs{,/**}',
            '!node_modules{,/**}',
            '!prepared{,/**}',
            '!CONTRIBUTING.md',
            '!LICENSE.md',
            '!README.md',
            '!gulpfile.js',
            '!netlify.toml',
            '!package.json',
            '!package-lock.json',
	'!fonts{,/**}',
	'!pictures/**',
        ])
        .pipe(replace(
            /(<link rel="stylesheet" href=")(node_modules\/shower-)([^\/]*)\/(.*\.css">)/g,
            '$1shower/themes/$3/$4', { skipBinary: true }
        ))
        .pipe(replace(
            /(<script src=")(node_modules\/shower-core\/)(shower.min.js"><\/script>)/g,
            '$1shower/$3', { skipBinary: true }
        )).pipe(replace(
            /(<script type="text\/javascript" src=")(node_modules\/mathjax\/)(MathJax.js" async><\/script>)/g,
            '$1mathjax/$3', { skipBinary: true }
	)).pipe(debug(
        )).pipe(mustache({
	    signature_comparison_table: fs.readFileSync("pictures/substorms/signature_comparison_table.html")
	}));

    const core = gulp.src([
            'shower.min.js'
        ], {
            cwd: 'node_modules/shower-core'
        })
        .pipe(rename( (path) => {
            path.dirname = 'shower/' + path.dirname;
        }));

    const mathjax = gulp.src([
            'mathjax/**'
        ], {
            cwd: 'node_modules'
        }).pipe(rename( (path) => {
            path.dirname = 'mathjax/' + path.dirname;
        }));

    const dejavu = gulp.src([
            'ttf/**'
        ], {
            cwd: 'node_modules/dejavu-fonts-ttf'
        }).pipe(rename( (path) => {
            path.dirname = 'fonts/' + path.dirname;
        }));

    const material = gulp.src([
            '**', '!package.json'
        ], {
            cwd: 'node_modules/shower-material'
        })
        .pipe(rename( (path) => {
            path.dirname = 'shower/themes/material/' + path.dirname;
        }))

    const ribbon = gulp.src([
            '**', '!package.json'
        ], {
            cwd: 'node_modules/shower-ribbon'
        })
        .pipe(rename( (path) => {
            path.dirname = 'shower/themes/ribbon/' + path.dirname;
        }));

    const noribbon = gulp.src([
            '**', '!package.json'
        ], {
            cwd: 'node_modules/shower-noribbon'
        })
        .pipe(rename( (path) => {
            path.dirname = 'shower/themes/noribbon/' + path.dirname;
        }));

    let plot_scripts=[
	{
	    script:'pictures/substorms/plot_substorm_convolution*.py',
	    dest:'prepared/pictures/substorms',
	    depends:'pictures/substorms/plot_substorm_convolution.py'
	},
	{
	    script:'pictures/substorms/plot_all*_tiled_onsetcomp_sea.py',
	    dest:'prepared/pictures/substorms',
	    depends:'pictures/substorms/plot_all_all_tiled_onsetcomp_sea.py'
	},
	{
	    script:'pictures/substorms/plot_*.py',
	    dest:'prepared/pictures/substorms',
	}]

    const plots=make_cp_pipeline('python',/^plot_(.+)\.py$/,'$1.svg',plot_scripts)

    let generator_scripts=[
	{
	    script:'pictures/**/write_*.py',
	    dest:'prepared/pictures',
	}]

    const generators=make_cp_pipeline('python',/^write_(.+)\.py$/,'$1.html',generator_scripts)

    const pictures = gulp.src([
	'pictures/**.svg',
	'pictures/**.png',
	'pictures/**.jpg'
    ]).pipe(rename( (path) => {
	path.dirname = 'pictures'
    }));

    const movies=gulp.src([
	'movies/**/*.{mp4,m4v}'
    ]).pipe(rename( (path) => {
	path.dirname = 'movies'
    }));

    const themes = merge(material, ribbon, noribbon)
        .pipe(replace(
            /(<script src=")(\/shower-core\/)(shower.min.js"><\/script>)/,
            '$1../../$3', { skipBinary: true }
        ));

    return merge(shower,core,themes,plots,generators,pictures,movies,mathjax,dejavu)
        .pipe(gulp.dest('prepared'));

});

gulp.task('clean', () => {
    return del('prepared/**');
});

gulp.task('zip', () => {
    return gulp.src('prepared/**')
        .pipe(zip('archive.zip'))
        .pipe(gulp.dest('.'));
});

gulp.task('upload', () => {
    return pages.publish('prepared')
});

gulp.task('archive', gulp.series(
    'prepare',
    'zip',
    'clean'
));

gulp.task('publish', gulp.series(
    'prepare',
    'upload',
    'clean'
));

gulp.task('serve', () => {
    sync.init({
        ui: false,
        notify: false,
        port: 3000,
        server: {
            baseDir: 'prepared'
        }
    });

    gulp.watch('index.html',gulp.series('prepare'));

    gulp.watch('index.html').on('change', () => {
	
        sync.reload();
    });
});

var makePictures = function (executable,matchRule,replaceRule) {
    return through.obj(function (vinylFileIn, encoding, callback) {

	// 1. clone new vinyl file for manipulation
	// (See https://github.com/wearefractal/vinyl for vinyl attributes and functions)
	var transformedFile = vinylFileIn.clone();

	//console.log(vinylFile.basename)

	// 2. set new contents
	// * contents can only be a Buffer, Stream, or null
	// * This allows us to modify the vinyl file in memory and prevents the need to write back to the file system.

	if(matchRule.test(vinylFileIn.basename))
	{
	    console.log(vinylFileIn.basename)
	    scriptname=String(vinylFileIn.basename)
	    var cwd=String(vinylFileIn.dirname)
	    console.log(cwd)
	    var process=cp.spawn(executable,[scriptname],options={'cwd':cwd})
	    
	    var lineReader = readline.createInterface(process.stdout, process.stdin);
	    lineReader.on('line', function(line) {
		console.log('Line: ' + line);
	    });
	    
	    var lineReaderErr = readline.createInterface(process.stderr, process.stdin);
	    lineReaderErr.on('line',  function(line) {
		console.error('Line: ' + line);
	    });

	    process.on('close', function(code,signal){
		newfilename=vinylFileIn.basename.replace(matchRule,replaceRule);
		console.log(newfilename)
		transformedFile = vinylFile.readSync(newfilename,
						     options={'cwd':cwd});
		// 3. pass along transformed file for use in next `pipe()`
		callback(null, transformedFile);
	    })
	}
	else
	{
	    // 3. pass along transformed file for use in next `pipe()`
	    callback(null, transformedFile);
	}

    });
}
