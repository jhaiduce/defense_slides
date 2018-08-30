const del = require('del');
const gulp = require('gulp');
const merge = require('merge-stream');
const rename = require('gulp-rename');
const replace = require('gulp-replace');
const zip = require('gulp-zip');
const pages = require('gh-pages');
const sync = require('browser-sync').create();
const cp=require('child_process')
const changed = require('gulp-changed');
const through = require('through2');
const vinylFile = require('vinyl-file')
var readline = require('readline');

gulp.task('prepare', () => {

    const shower = gulp.src([
            '**',
            '!docs{,/**}',
            '!node_modules{,/**}',
            '!prepared{,/**}',
            '!CONTRIBUTING.md',
            '!LICENSE.md',
            '!README.md',
            '!gulpfile.js',
            '!netlify.toml',
            '!package.json',
            '!package-lock.json'
        ])
        .pipe(replace(
            /(<link rel="stylesheet" href=")(node_modules\/shower-)([^\/]*)\/(.*\.css">)/g,
            '$1shower/themes/$3/$4', { skipBinary: true }
        ))
        .pipe(replace(
            /(<script src=")(node_modules\/shower-core\/)(shower.min.js"><\/script>)/g,
            '$1shower/$3', { skipBinary: true }
        ));

    const core = gulp.src([
            'shower.min.js'
        ], {
            cwd: 'node_modules/shower-core'
        })
        .pipe(rename( (path) => {
            path.dirname = 'shower/' + path.dirname;
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

    const pictures = gulp.src([
	'pictures/**'
    ]).pipe(
	changed('prepared/pictures')
    ).pipe(makePictures()
    ).pipe(rename( (path) => {
	path.dirname = 'pictures' + path.dirname
    }));

    const themes = merge(material, ribbon, noribbon)
        .pipe(replace(
            /(<script src=")(\/shower-core\/)(shower.min.js"><\/script>)/,
            '$1../../$3', { skipBinary: true }
        ));

    return merge(shower, core, themes, pictures)
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
            baseDir: '.'
        }
    });
    gulp.watch('index.html').on('change', () => {
        sync.reload();
    });
});

var makePictures = function () {
    return through.obj(function (vinylFileIn, encoding, callback) {

	// 1. clone new vinyl file for manipulation
	// (See https://github.com/wearefractal/vinyl for vinyl attributes and functions)
	var transformedFile = vinylFileIn.clone();

	//console.log(vinylFile.basename)

	// 2. set new contents
	// * contents can only be a Buffer, Stream, or null
	// * This allows us to modify the vinyl file in memory and prevents the need to write back to the file system.

	if(/^plot_(.+)\.py$/.test(vinylFileIn.basename))
	{
	    console.log(vinylFileIn.basename)
	    scriptname=String(vinylFileIn.basename)
	    var cwd=String(vinylFileIn.dirname)
	    console.log(cwd)
	    var process=cp.spawn('python',[scriptname],options={'cwd':cwd})
	    
	    var lineReader = readline.createInterface(process.stdout, process.stdin);
	    lineReader.on('line', function(line) {
		console.log('Line: ' + line);
	    });

	    process.on('close', function(code,signal){
		newfilename=vinylFileIn.basename.replace(/^plot_(.+).py$/,'$1.svg');
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
