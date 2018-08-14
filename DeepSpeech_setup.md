# DeepSpeech setup

It's been a few months since I have built DeepSpeech (today is August 13th, 2018), so these instructions probably need to be updated when I have time.
They are for building DeepSpeech on Debian or a derivative, but should be fairly easy to translate to other systems by just changing the package manager and package names.

```
[~]$ sudo apt-get install pkg-config zip g++ zlib1g-dev unzip
```
Apparently you need bazel in order to build bazel, so download a copy and unzip it
```
[~]$ wget https://github.com/bazelbuild/bazel/releases/download/0.4.5/bazel-0.4.5-dist.zip
[~]$ unzip -d bazel-0.4.5-dist bazel-0.4.5-dist.zip
[~]$ cd bazel-0.4.5-dist
```
The script is in 555 mode when you unzip it, so you have to make it writable
```
[~/bazel-0.4.5-dist]$ chmod a+w scripts/bootstrap/compile.sh
```
If you are building for the Raspberry Pi, do these things (note that DeepSpeech did not run very well on the Raspberry Pi the last time I checked. The language model was too large to fit in memory, and without it DeepSpeech just returns raw phonemes):

* vi scripts/bootstrap/compile.sh
* Goto line 117 and add -J-Xmx500M
* Save and quit

It also sounds like maybe the cc_configure.bzl script has some trouble figuring out the platform, so you give it a little help by editing the _get_cpu_value function and just tell it to always return “arm”

Now build it
```
[~/bazel-0.4.5-dist]$ ./compile.sh
Build successful! Binary is here: ~/bazel-0.4.5-dist/output/bazel
[~/bazel-0.4.5-dist]$ sudo cp -iv output/bazel /usr/local/bin/
[~/bazel-0.4.5-dist]$ cd ..
[~]$ git clone https://github.com/mozilla/tensorflow.git
[~]$ git clone https://github.com/mozilla/DeepSpeech.git
[~]$ cd tensorflow/
[~/tensorflow]$ ln -s ../DeepSpeech/native_client/ ./
[~/tensorflow]$ ./configure
[~/tensorflow]$ bazel build -c opt --copt=-O3 //native_client:libctc_decoder_with_kenlm.so
[~/tensorflow]$ bazel build --config=monolithic -c opt --copt=-O3 --copt=-fvisibility=hidden --incompatible_load_argument_is_label=false //native_client:libdeepspeech.so //native_client:deepspeech_utils //native_client:libctc_decoder_with_kenlm.so //native_client:generate_trie
[~/tensorflow]$ cd native_client
[~/tensorflow/native_client]$ make deepspeech
[~/tensorflow/native_client]$ PREFIX=/usr/local sudo make install
[~/tensorflow/native_client]$ make bindings
[~/tensorflow/native_client]$ pip install dist/deepspeech-*.whl 
```
I recommend using PocketSphinx for passive listening and DeepSpeech for active listening. To use it as the active listener with Naomi, you will need to add a section like this to your profile.yml file:
```
active_stt:
  engine: deepspeech-stt
deepspeech:
  model: '/home/user/models/output_graph.pb'
  alphabet: '/home/user/models/alphabet.txt'
  language_model: '/home/user/models/lm.binary'
  trie: '/home/user/models/trie'
```
